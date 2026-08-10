# Read API v1

- Status: Contract baseline; implementation pending
- Transport: HTTPS, JSON, read-only
- Data authority: exact sealed release, never a mutable database head

## Contract/version distinction

`v1` in `/api/v1` is the API contract version. `releaseId` is the data version. They are independent and must never be collapsed into one `version` field.

Every successful resource response identifies:

```json
{
  "apiVersion": "v1",
  "release": {
    "releaseId": "v49-YYYYMMDD.N",
    "manifestSha256": "64 lowercase hex",
    "schemaVersion": "archive-release/v1"
  },
  "data": {}
}
```

A client may resolve `current` once, but the repository must then use the returned exact `releaseId` and manifest hash for every request. `current` is never a substitute for evidence-level version pinning.

## Read-only surface

The API supports only `GET`, `HEAD`, and `OPTIONS`. There are no ingest, scrape, review, rights override, gate, export-generation, release promotion, or mutation endpoints under `/api/v1`.

| Method and path | Purpose |
|---|---|
| `GET /api/v1/releases/current` | Resolve the recommended sealed release once. |
| `GET /api/v1/releases/{releaseId}` | Exact release descriptor and availability. |
| `GET /api/v1/releases/{releaseId}/manifest` | Canonical release manifest or verified projection of it. |
| `GET /api/v1/releases/{releaseId}/archive/overview` | Exact precomputed counts with named units. |
| `GET /api/v1/releases/{releaseId}/folder-types` | Folder type summaries. |
| `GET /api/v1/releases/{releaseId}/folders` | Paginated folder summaries and filters. |
| `GET /api/v1/releases/{releaseId}/folders/{folderId}` | One folder detail without embedded bulk membership. |
| `GET /api/v1/releases/{releaseId}/folders/{folderId}/surfaces` | Paginated rights-safe folder members. |
| `GET /api/v1/releases/{releaseId}/surfaces/{surfaceId}` | One rights-safe surface detail and evidence summary. |
| `GET /api/v1/releases/{releaseId}/search` | Release-pinned multi-scope Search. |
| `GET /api/v1/releases/{releaseId}/trace/atlas` | Frozen atlas summary, matrices, and declared units. |
| `GET /api/v1/releases/{releaseId}/trace/objects` | Paginated TRACE object summaries by explicit layer. |
| `GET /api/v1/releases/{releaseId}/trace/objects/{objectId}/neighborhood` | Verified, release-bound graph neighborhood. |
| `GET /api/v1/releases/{releaseId}/trace/relation-types` | Published relation registry definitions. |
| `GET /api/v1/releases/{releaseId}/trace/relation-types/{relationTypeId}` | One published relation definition and evidence policy. |

## Archive DTO boundary

API DTOs are stable read models and do not reuse PostgreSQL rows or expose schema/table names.

`SurfaceSummary` contains only list/search fields: ID, title, display date, principal credited labels, place/medium/type labels, rights-safe thumbnail state, source label, and publication layer.

The exposed `surfaceId` is a durable public route identifier, not the canonical `archive_object_id`. A sealed release also freezes alias/redirect/split/withdrawal resolution; read-time identity never consults mutable canonical crosswalk rows.

`SurfaceDetail` may include:

- the presentation bundle needed by current visual pages;
- ordered typed credits, media, types, subjects, places, and collections;
- rights-safe digital representations and explicit image state;
- source/evidence/citation links permitted for publication;
- ordered metadata tables and dossier links;
- TRACE summary and routes, not an embedded whole catalog.

It never contains raw provider payloads, private workflow notes, database keys, unrestricted URLs, or rights-held bytes.

`FolderDetail` contains narrative metadata, related-folder summaries, authority reference summaries, and exact named counts. Members use the separate paginated endpoint; it does not embed thousands of surface IDs.

## TRACE semantics

`GET .../trace/objects` requires or defaults an explicit `layer`:

- `active`: the sealed active publication layer;
- `review`: an explicitly published review layer, independent of whether a workflow case is currently in review;
- `auxiliary`: a context-only publication layer.

The returned summary is a discriminated union and always carries `layer`. Metric-specific eligibility is reported only for a named release metric; there is no universal canonical `countEligible` implication. The atlas and default neighborhood expose accepted relation types only.

An unregistered relation is not an `OTHER` type and is not a normal review DTO. It remains in raw/workflow systems outside the public read API. If an accepted release asset contains an unknown label, the resource fails with `INTEGRITY_FAILURE` rather than returning partial graph data.

The API preserves these separately named units:

- `totalGraphEdges` for all graph edges;
- `activeObjectRelationMemberships` for accepted object-to-relation memberships;
- counts per relation family;
- active, review, and auxiliary object counts.

## Search contract

`GET .../search` accepts:

- `q`: trimmed UTF-8 query, required, bounded length;
- `scope=archive|trace|relation|all`;
- registered filters such as region, decade, medium concept, relation family, folder, and rights-visible image state;
- `first` and `after` for pagination;
- one allowlisted stable sort.

Results use a discriminated union (`archive`, `trace`, or `relation`) and carry stable IDs, highlights derived from rights-safe read models, and explicit routes. Search documents are release projections and cannot write back into canonical tables.

v48 reconciliation keeps two existing populations distinct: archive Search has 8,636 unique IDs and canonical JSON/active TRACE has 15,923. Their intersection is 2,585; Search-only is 6,051; TRACE-only is 13,338; the union is 21,974. Search is therefore not a subset of TRACE.

Only the canonical JSON/TRACE cohort seeds v49 migration. The Search-only derived population is not copied into canonical data. A v49 Search projection is generated from its sealed release cohort, so 8,636 is an integrity/reconciliation fact rather than a required v49 result count.

No query may trigger live provider scraping. Empty queries do not load bulk indexes, preserving the current useful on-demand behavior.

## Pagination and cursors

- Default `first` is 50; maximum is 100.
- Pagination is keyset-based. Offset pagination is not part of v1.
- Every stable sort ends with a unique public ID tie-breaker.
- A cursor binds release ID, manifest hash, endpoint/resource kind, normalized filters, sort, and final key.
- Reusing a cursor with another release or filter set returns `409 RELEASE_VERSION_MISMATCH` or `400 INVALID_CURSOR` as appropriate.
- `totalExact` appears only when the sealed release contains a precomputed exact count for that exact scope. A page length is never labeled as total.

List envelope:

```json
{
  "apiVersion": "v1",
  "release": {
    "releaseId": "v49-YYYYMMDD.N",
    "manifestSha256": "...",
    "schemaVersion": "archive-release/v1"
  },
  "data": {
    "nodes": [],
    "pageInfo": {
      "hasNextPage": false,
      "nextCursor": null,
      "totalExact": 0
    }
  }
}
```

## Errors

Errors use `application/problem+json`:

```json
{
  "type": "https://modern-gd.example/problems/integrity-failure",
  "title": "Release integrity failure",
  "status": 503,
  "code": "INTEGRITY_FAILURE",
  "detail": "Relation registry digest does not match the manifest",
  "instance": "/api/v1/releases/v49-.../trace/atlas",
  "requestId": "opaque request id",
  "releaseId": "v49-..."
}
```

| Status | Code examples | Meaning |
|---:|---|---|
| 400 | `INVALID_ARGUMENT`, `INVALID_CURSOR` | Input cannot be validated. |
| 404 | `RELEASE_NOT_FOUND`, `NOT_FOUND` | Exact release or resource does not exist. |
| 409 | `RELEASE_VERSION_MISMATCH` | Cursor, selector, or dependency belongs to another release. |
| 503 | `INTEGRITY_FAILURE`, `UNREGISTERED_RELATION`, `UNAVAILABLE` | Hash/schema/registry/release verification failed or exact release is unavailable. |

`NOT_FOUND`, `UNAVAILABLE`, and `INTEGRITY_FAILURE` are never collapsed to an empty success or `undefined`. A hash mismatch never falls back to `current`, v48, or a fixture.

## Caching and integrity

- Exact sealed endpoints return a strong ETag derived from manifest hash plus resource hash and use `Cache-Control: public, max-age=31536000, immutable` where rights permit public caching.
- The `current` resolver uses short caching or revalidation and returns the exact descriptor. Publishing it is a release-layer CAS operation; the read API never updates it.
- Responses include `X-Archive-Release-Id` and `X-Archive-Manifest-Sha256` for diagnostics; the JSON envelope remains authoritative.
- Repository caches and request deduplication key on exact release and manifest hash.
- The service validates database projection identity or immutable asset hash before serving. A permanently invalid release is quarantined from `current`.

## `ArchiveRepository` mapping

| Repository method | API resource |
|---|---|
| `getOverview` | `/archive/overview` |
| `listFolderTypes` | `/folder-types` |
| `listFolders` | `/folders` |
| `getFolder` | `/folders/{folderId}` |
| `listFolderMembers` | `/folders/{folderId}/surfaces` |
| `getSurface` | `/surfaces/{surfaceId}` |
| `search` | `/search` |
| `getTraceAtlas` | `/trace/atlas` |
| `listTraceObjects` | `/trace/objects` |
| `getTraceNeighborhood` | `/trace/objects/{objectId}/neighborhood` |
| `listRelationTypes` | `/trace/relation-types` |
| `getRelationType` | `/trace/relation-types/{relationTypeId}` |

The HTTP and immutable-release adapters must return equivalent DTOs and errors for the same release contract fixture.

## Compatibility policy

- Additive optional fields may appear within v1 only after schema/consumer contract tests pass.
- Removing, renaming, changing meaning, changing unit, or changing nullability requires a new API contract version.
- Data changes use a new release ID, not a new API version.
- Relation registry or rights policy changes create a new release and digest even if DTO shape is unchanged.
- A client must reject an unknown major schema/API version.

## Prototype boundary

Contract validation in the prototype phase uses a small pinned fixture and focused repository tests. It does not require or permit full `next build`, `next dev`, browser automation, data export, or full-project TypeScript. Production build/browser gates begin only after the repository and data release pass their independent promotion gates.
