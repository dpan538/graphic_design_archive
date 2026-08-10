# Read API v1

- Status: Contract baseline; implementation pending
- Transport: HTTPS, JSON, read-only
- Data authority: exact sealed research release plus, for visual-bearing resources, one compatible sealed visual registry; never a mutable database head

## Contract/version distinction

`v1` in `/api/v1` is the API contract version. `researchReleaseId` and `visualRegistryVersion` are independent data versions and must never be collapsed into one `version` field.

Every successful resource response identifies:

```json
{
  "apiVersion": "v1",
  "researchRelease": {
    "researchReleaseId": "v49-research-YYYYMMDD.N",
    "researchManifestSha256": "64 lowercase hex",
    "schemaVersion": "archive-research-release/v1"
  },
  "visualRegistry": {
    "visualRegistryVersion": "v49-visual-YYYYMMDD.N",
    "registrySha256": "64 lowercase hex",
    "compatibleResearchReleaseId": "v49-research-YYYYMMDD.N",
    "compatibleResearchManifestSha256": "64 lowercase hex",
    "schemaVersion": "archive-visual-registry/v1"
  },
  "data": {}
}
```

A client may resolve the research and visual `current` pointers once, verify their compatibility, and then use both exact pairs for every visual-bearing request. Each pointer is independently CAS-controlled. `current` is never a substitute for evidence-level version pinning, and cross-pair fallback is prohibited.

## Read-only surface

The API supports only `GET`, `HEAD`, and `OPTIONS`. There are no ingest, scrape, review, rights override, gate, export-generation, release promotion, or mutation endpoints under `/api/v1`.

| Method and path | Purpose |
|---|---|
| `GET /api/v1/releases/current` | Resolve the recommended sealed research pair once. |
| `GET /api/v1/visual-registries/current` | Resolve the recommended sealed visual pair once. |
| `GET /api/v1/releases/{researchReleaseId}` | Exact research-release descriptor and availability. |
| `GET /api/v1/releases/{researchReleaseId}/manifest` | Canonical research manifest or verified projection of it. |
| `GET /api/v1/visual-registries/{visualRegistryVersion}` | Exact visual-registry descriptor and compatible research pair. |
| `GET /api/v1/visual-registries/{visualRegistryVersion}/manifest` | Canonical visual-registry manifest or verified projection. |
| `GET /api/v1/releases/{researchReleaseId}/archive/overview` | Exact precomputed counts with named units. |
| `GET /api/v1/releases/{researchReleaseId}/folder-types` | Folder type summaries. |
| `GET /api/v1/releases/{researchReleaseId}/folders` | Paginated folder summaries and filters. |
| `GET /api/v1/releases/{researchReleaseId}/folders/{folderId}` | One folder detail without embedded bulk membership. |
| `GET /api/v1/releases/{researchReleaseId}/folders/{folderId}/surfaces` | Paginated rights-safe folder members. |
| `GET /api/v1/releases/{researchReleaseId}/surfaces/{surfaceId}` | One rights-safe surface detail and evidence summary. |
| `GET /api/v1/releases/{researchReleaseId}/search` | Research-release-pinned multi-scope Search. |
| `GET /api/v1/releases/{researchReleaseId}/trace/atlas` | Frozen atlas summary, matrices, and declared units. |
| `GET /api/v1/releases/{researchReleaseId}/trace/objects` | Paginated TRACE object summaries by explicit layer. |
| `GET /api/v1/releases/{researchReleaseId}/trace/objects/{objectId}/neighborhood` | Verified, research-release-bound graph neighborhood. |
| `GET /api/v1/releases/{researchReleaseId}/trace/relation-types` | Published relation registry definitions. |
| `GET /api/v1/releases/{researchReleaseId}/trace/relation-types/{relationTypeId}` | One published relation definition and evidence policy. |
| `GET /api/v1/releases/{researchReleaseId}/relations/{relationId}` | One normalized semantic relation with eligible supporting/challenging claim summaries. |
| `GET /api/v1/releases/{researchReleaseId}/claims/{claimId}` | One rights-safe claimant-bound claim and evidence/citation locators. |
| `GET /api/v1/releases/{researchReleaseId}/corpora` | Versioned research corpus summaries and selection policies. |
| `GET /api/v1/releases/{researchReleaseId}/corpora/{corpusVersionId}` | Exact corpus descriptor, counts, missingness and method hashes. |

All read-model endpoints below the exact research-release path require the exact `Archive-Visual-Registry-Version` and `Archive-Visual-Registry-Sha256` request headers and return both envelope members. They reject absent, mismatched, unsealed, or incompatible visual pairs; they never infer visual `current`. The standalone research/visual descriptor and manifest endpoints are the only discovery exceptions.

## Archive DTO boundary

API DTOs are stable read models and do not reuse PostgreSQL rows or expose schema/table names.

`SurfaceSummary` contains only list/search fields: ID, title, display date, principal credited labels, place/medium/type labels, fail-closed visual-delivery state, source label, and publication layer.

The exposed `surfaceId` is a durable public route identifier, not the canonical `archive_object_id`. A sealed release also freezes alias/redirect/split/withdrawal resolution; read-time identity never consults mutable canonical crosswalk rows.

`SurfaceDetail` may include:

- the presentation bundle needed by current visual pages;
- ordered typed credits, media, types, subjects, places, and collections;
- rights-safe digital representations and explicit image state;
- source/evidence/citation links permitted for publication;
- ordered metadata tables and dossier links;
- TRACE summary and routes, not an embedded whole catalog.

It never contains raw provider payloads, private workflow notes, database keys, unrestricted URLs, rights-held bytes, or pixel/thumbnail/image-service/embed URLs when rights/provider state is unknown, missing, conflicting or stale. API/IIIF availability, redirects and endpoint health never grant delivery.

`FolderDetail` contains narrative metadata, related-folder summaries, authority reference summaries, and exact named counts. Members use the separate paginated endpoint; it does not embed thousands of surface IDs.

## TRACE semantics

`GET .../trace/objects` requires or defaults an explicit `layer`:

- `active`: the sealed active publication layer;
- `review`: an explicitly published review layer, independent of whether a workflow case is currently in review;
- `auxiliary`: a context-only publication layer.

The returned summary is a discriminated union and always carries `layer` and exact corpus identity. Metric-specific eligibility is reported only for a named release metric; there is no universal canonical `countEligible` implication. The atlas and default neighborhood expose sealed TRACE projections of eligible semantic relations/claims, not a claim that every projected triple is a documented fact.

An unregistered relation is not an `OTHER` type and is not a normal review DTO. It remains in raw/workflow systems outside the public read API. If an accepted release asset contains an unknown label, the resource fails with `INTEGRITY_FAILURE` rather than returning partial graph data.

The API preserves these separately named units:

- `totalGraphEdges` for all graph edges;
- `activeObjectRelationMemberships` for accepted object-to-relation memberships;
- normalized semantic relations, claimant-bound claims, and projected TRACE edges as different units;
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
- A cursor binds research release ID/hash, compatible visual-registry version/hash when applicable, endpoint/resource kind, corpus, normalized filters, sort, and final key.
- Reusing a cursor with another research/visual pair, corpus or filter set returns `409 RELEASE_VERSION_MISMATCH` or `400 INVALID_CURSOR` as appropriate.
- `totalExact` appears only when the sealed release contains a precomputed exact count for that exact scope. A page length is never labeled as total.

List envelope:

```json
{
  "apiVersion": "v1",
  "researchRelease": {
    "researchReleaseId": "v49-research-YYYYMMDD.N",
    "researchManifestSha256": "...",
    "schemaVersion": "archive-research-release/v1"
  },
  "visualRegistry": {
    "visualRegistryVersion": "v49-visual-YYYYMMDD.N",
    "registrySha256": "...",
    "schemaVersion": "archive-visual-registry/v1"
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
  "researchReleaseId": "v49-research-...",
  "visualRegistryVersion": "v49-visual-..."
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

- Exact sealed endpoints return a strong ETag derived from the exact research pair, compatible visual pair when applicable, and resource hash; immutable caching is used only where the sealed visual decision permits it.
- Each `current` resolver uses short caching or revalidation and returns an exact descriptor. Publishing either pointer is a CAS operation; the read API never updates it.
- Responses include research-release/manifest and visual-registry/hash diagnostic headers; the JSON envelope remains authoritative.
- Repository caches and request deduplication key on the exact research/visual pair and corpus.
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
| `getRelation` | `/relations/{relationId}` |
| `getClaim` | `/claims/{claimId}` |
| `listCorpora` | `/corpora` |
| `getCorpus` | `/corpora/{corpusVersionId}` |

The HTTP and immutable-release adapters must return equivalent DTOs and errors for the same exact research/visual pair contract fixture.

## Compatibility policy

- Additive optional fields may appear within v1 only after schema/consumer contract tests pass.
- Removing, renaming, changing meaning, changing unit, or changing nullability requires a new API contract version.
- Research data/claim/corpus changes use a new research release, not a new API version.
- Visual policy, health, obligation or takedown changes use a new visual-registry version or restrictive override; they do not rewrite the research release.
- A client must reject an unknown major schema/API version.

## Machine-readable publication

Canonical, version-independent identifiers use the class-specific URI templates in ADR 0004 for objects, semantic relations, claims, corpora, research releases and visual registries. Public surface routes are aliases/resolvers, not canonical object identity.

Every HTML object/relation/claim resource has server-rendered crawlable metadata, one canonical URL and a JSON-LD alternate. Versioned JSON Schemas cover research/visual manifests, envelopes, resources, cursors, problems and change-feed items. Normative mappings define Linked Art for archive resources, PROV-O for evidence/claims/derivations and DCAT for dataset/distribution release metadata. A release diff/change feed and sitemap/robots policy preserve merges, splits, withdrawals, corpus changes and takedown-safe discovery.

These are contract requirements only. The Phase 1B audit measured zero `/api/v1` routes, zero release/API schemas, zero JSON-LD/DCAT/change-feed/sitemap implementations and zero CI workflows; implementation readiness remains false.

## Prototype boundary

Contract validation in the prototype phase uses a small pinned fixture and focused repository tests. It does not require or permit full `next build`, `next dev`, browser automation, data export, or full-project TypeScript. Production build/browser gates begin only after the repository and data release pass their independent promotion gates.
