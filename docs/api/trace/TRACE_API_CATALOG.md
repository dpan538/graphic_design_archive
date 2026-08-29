# TRACE API catalog

This catalog records the complete implemented API surface of exactly three TRACE functions: Context Canvas, Spacetime, and Exploration. Search is outside TRACE. Shared TRACE infrastructure is cataloged separately and does not create a fourth function.

```text
TRACE
├── Context Canvas
├── Spacetime
└── Exploration
    ├── Validated Exploration
    └── Open Inquiry
```

`TRACE_TOP_LEVEL_FUNCTION_COUNT=3`

`TRACE_LOGICAL_ROUTE_TEMPLATE_COUNT=75`

`TRACE_EXPANDED_METHOD_ROUTE_PAIR_COUNT=228`

The JSON catalog is the machine authority. Each record below repeats its request, response, implementation, state, frontend, limitation, and nonclaim contract.

## TRACE Function 1

### `trace.f1.context.object-context.v1`

- Function/layer: `TRACE_FUNCTION_1` / `CONTEXT_CANVAS`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/v1/releases/{release}/trace/objects/{id}/context`
- Implementation status: `IMPLEMENTED_GOVERNED_READ_ONLY`
- Request schema: Release path and public stable object ID; an exact release requires Archive-Research-Manifest-Sha256; no body or query parameters. (`frontend/src/features/trace-v49/context/governed/read-api-runtime.server.ts`; `tryReadGovernedContextApiResource`)
- Response schema: Read API v1 envelope containing PublicContextDataset. (`frontend/src/features/trace-v49/context/governed/types.ts`; `PublicContextDataset`)
- Source route: `frontend/src/app/api/v1/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/context/governed/read-api-runtime.server.ts`
- Service/repository: `frontend/src/features/trace-v49/context/governed/reader.server.ts`
- Test: `frontend/scripts/verify-context-api-v1.mjs`
- Authentication: None; governed public release identity is enforced through the release pair and optional integrity header.
- Pagination: None.
- Sorting: Deterministic committed projection order.
- Caching: Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.
- Loading state: SSR or request pending.
- Empty state: availability=empty is a valid governed result.
- Partial state: No partial protocol state.
- Error state: 400 invalid ID; 404 held/unknown/unavailable; 409 release mismatch; 503 integrity failure.
- Frontend use: Context Canvas can load the selected public record and governed medium, theme, and movement-context representations; the current workspace reads the same governed source server-side.
- Limitations: No pagination or client sorting. The workspace is not linked into public navigation by this integration.
- Explicit nonclaims: Project-curated context is not an influence or semantic edge. Held UUIDs and full-corpus data are not exposed. Context Canvas is independent from Exploration.

## TRACE Function 2

### `trace.f2.spacetime.atlas.v1`

- Function/layer: `TRACE_FUNCTION_2` / `SPACETIME`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/v1/releases/{release}/trace/spacetime/atlas`
- Implementation status: `IMPLEMENTED_GOVERNED_READ_ONLY`
- Request schema: Exactly one required period query parameter; no body. (`frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts`; `atlas request`)
- Response schema: Read API v1 envelope containing PublicSpacetimeAtlasDataset. (`frontend/src/features/trace-v49/spacetime/governed/types.ts`; `PublicSpacetimeAtlasDataset`)
- Source route: `frontend/src/app/api/v1/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts`
- Service/repository: `frontend/src/features/trace-v49/spacetime/governed/reader.server.ts`
- Test: `frontend/scripts/verify-spacetime-api-v1.mjs`
- Authentication: None; exact-release requests require the committed release manifest identity.
- Pagination: None.
- Sorting: Committed geography/mark order.
- Caching: Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.
- Loading state: Atlas request pending after period selection.
- Empty state: A period with no governed marks is valid empty data.
- Partial state: No partial protocol state.
- Error state: 400 query error; 404 period/release error; 503 integrity failure.
- Frontend use: Loads governed aggregate geographic marks for one selected period.
- Limitations: Governed periods and geography identities are fixed by the committed projection. The workspace is not linked into public navigation by this integration.
- Explicit nonclaims: Recorded region/date context is not an object coordinate or historical-presence claim. Aggregate marks do not assert movement, influence, or an Exploration association. realSemanticEdgeCount remains zero.

### `trace.f2.spacetime.geography-records.v1`

- Function/layer: `TRACE_FUNCTION_2` / `SPACETIME`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/v1/releases/{release}/trace/spacetime/geographies/{geographyId}/records`
- Implementation status: `IMPLEMENTED_GOVERNED_READ_ONLY`
- Request schema: Geography path ID; exactly one period; optional first 1..100 (default 24) and projection-bound after cursor up to 2048 characters. (`frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts`; `geography-record request`)
- Response schema: Read API v1 envelope containing PublicSpacetimeRecordPage. (`frontend/src/features/trace-v49/spacetime/governed/types.ts`; `PublicSpacetimeRecordPage`)
- Source route: `frontend/src/app/api/v1/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts`
- Service/repository: `frontend/src/features/trace-v49/spacetime/governed/reader.server.ts`
- Test: `frontend/scripts/verify-spacetime-api-v1.mjs`
- Authentication: None; exact-release requests require the committed release manifest identity.
- Pagination: Deterministic cursor pagination; first defaults to 24 and is bounded 1..100; hasNextPage/endCursor signal continuation.
- Sorting: Committed projection order; no caller-selected sort.
- Caching: Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.
- Loading state: Selected-geography page request pending.
- Empty state: A zero-record page is valid.
- Partial state: hasNextPage=true is an explicit partial state until load-more completes.
- Error state: 400 invalid query/cursor; 404 geography/period/release; 503 integrity failure.
- Frontend use: Loads and incrementally extends the selected geography's recorded-object list.
- Limitations: Governed periods and geography identities are fixed by the committed projection. The workspace is not linked into public navigation by this integration.
- Explicit nonclaims: Recorded region/date context is not an object coordinate or historical-presence claim. Aggregate marks do not assert movement, influence, or an Exploration association. realSemanticEdgeCount remains zero.

### `trace.f2.spacetime.periods.v1`

- Function/layer: `TRACE_FUNCTION_2` / `SPACETIME`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/v1/releases/{release}/trace/spacetime/periods`
- Implementation status: `IMPLEMENTED_GOVERNED_READ_ONLY`
- Request schema: Release path; no query or body. (`frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts`; `periods request`)
- Response schema: Read API v1 envelope containing PublicSpacetimePeriodsDataset. (`frontend/src/features/trace-v49/spacetime/governed/types.ts`; `PublicSpacetimePeriodsDataset`)
- Source route: `frontend/src/app/api/v1/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts`
- Service/repository: `frontend/src/features/trace-v49/spacetime/governed/reader.server.ts`
- Test: `frontend/scripts/verify-spacetime-api-v1.mjs`
- Authentication: None; exact-release requests require the committed release manifest identity.
- Pagination: None.
- Sorting: Committed period display order.
- Caching: Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.
- Loading state: Periods request pending.
- Empty state: An empty governed period inventory is displayable.
- Partial state: No partial protocol state.
- Error state: 400 query error; 404 release error; 503 integrity failure.
- Frontend use: Initializes the discrete Spacetime period selector.
- Limitations: Governed periods and geography identities are fixed by the committed projection. The workspace is not linked into public navigation by this integration.
- Explicit nonclaims: Recorded region/date context is not an object coordinate or historical-presence claim. Aggregate marks do not assert movement, influence, or an Exploration association. realSemanticEdgeCount remains zero.

## TRACE Function 3 — Validated Exploration

### `trace.f3.validated.v1.retired-catchall`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V1_RETIRED`
- Method: `GET, HEAD, OPTIONS, POST, PUT, PATCH, DELETE`
- Route: `/api/trace/v1/exploration/{...path}`
- Implementation status: `RETIRED_410`
- Request schema: Any request to the retired v1 root or catch-all. (`frontend/src/app/api/trace/v1/exploration/route.ts`; `retired request`)
- Response schema: HTTP 410 trace-exploration-api-retirement-v1 payload; HEAD is bodyless. (`frontend/src/app/api/trace/v1/exploration/route.ts`; `RETIREMENT_PAYLOAD`)
- Source route: `frontend/src/app/api/trace/v1/exploration/[...path]/route.ts`
- Handler: `frontend/src/app/api/trace/v1/exploration/[...path]/route.ts`
- Service/repository: `frontend/src/app/api/trace/v1/exploration/[...path]/route.ts`
- Test: `frontend/scripts/validate-trace-exploration-v2-http.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: None.
- Caching: Cache-Control: private, no-store; successor Link and Sunset headers.
- Loading state: No loading data contract; response is immediate retirement.
- Empty state: Not applicable.
- Partial state: Not applicable.
- Error state: Every method returns 410 API_VERSION_RETIRED; HEAD has no body.
- Frontend use: Compatibility-only retirement signal; clients must use v2.
- Limitations: OPTIONS intentionally returns the retirement payload rather than 204. No v1 data remains available.
- Explicit nonclaims: The retired catch-all is not an implemented product data surface. Retirement does not create a fourth function.

### `trace.f3.validated.v1.retired-root`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V1_RETIRED`
- Method: `GET, HEAD, OPTIONS, POST, PUT, PATCH, DELETE`
- Route: `/api/trace/v1/exploration`
- Implementation status: `RETIRED_410`
- Request schema: Any request to the retired v1 root or catch-all. (`frontend/src/app/api/trace/v1/exploration/route.ts`; `retired request`)
- Response schema: HTTP 410 trace-exploration-api-retirement-v1 payload; HEAD is bodyless. (`frontend/src/app/api/trace/v1/exploration/route.ts`; `RETIREMENT_PAYLOAD`)
- Source route: `frontend/src/app/api/trace/v1/exploration/route.ts`
- Handler: `frontend/src/app/api/trace/v1/exploration/route.ts`
- Service/repository: `frontend/src/app/api/trace/v1/exploration/route.ts`
- Test: `frontend/scripts/validate-trace-exploration-v2-http.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: None.
- Caching: Cache-Control: private, no-store; successor Link and Sunset headers.
- Loading state: No loading data contract; response is immediate retirement.
- Empty state: Not applicable.
- Partial state: Not applicable.
- Error state: Every method returns 410 API_VERSION_RETIRED; HEAD has no body.
- Frontend use: Compatibility-only retirement signal; clients must use v2.
- Limitations: OPTIONS intentionally returns the retirement payload rather than 204. No v1 data remains available.
- Explicit nonclaims: The retired catch-all is not an implemented product data surface. Retirement does not create a fourth function.

### `trace.f3.validated.v2.associations.get`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v2/exploration/associations/{associationId}`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: Association ID; no body/query. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2AssociationDto`)
- Response schema: ExplorationV2AssociationDto (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2AssociationDto`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.capabilities.get`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v2/exploration/capabilities`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: No body/query. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2CapabilitiesResponse`)
- Response schema: ExplorationV2CapabilitiesResponse (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2CapabilitiesResponse`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.categories.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v2/exploration/categories`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: No body/query. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2CategoriesResponse`)
- Response schema: ExplorationV2CategoriesResponse (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2CategoriesResponse`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.exports.manifest`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `POST, OPTIONS`
- Route: `/api/trace/v2/exploration/exports/manifest`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: JSON ExplorationV2ExportRequest; body <=65536 bytes. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2ExportRequest`)
- Response schema: ExplorationV2ExportManifestDto (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2ExportManifestDto`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.exports.png`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `POST, OPTIONS`
- Route: `/api/trace/v2/exploration/exports/png`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: JSON ExplorationV2ExportRequest; body <=65536 bytes. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2ExportRequest`)
- Response schema: image/png bytes with semantic/presentation/state/export headers (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `PNG bytes`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.exports.svg`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `POST, OPTIONS`
- Route: `/api/trace/v2/exploration/export/svg`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: JSON ExplorationV2ExportRequest; body <=65536 bytes. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2ExportRequest`)
- Response schema: image/svg+xml bytes with semantic/presentation/state/export headers (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `SVG bytes`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.maps.actions`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `POST, OPTIONS`
- Route: `/api/trace/v2/exploration/maps/{mapId}/actions`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: Map ID and JSON ExplorationV2ActionRequest; body <=65536 bytes. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2ActionRequest`)
- Response schema: ExplorationV2MapDto (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2MapDto`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.maps.create`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `POST, OPTIONS`
- Route: `/api/trace/v2/exploration/maps`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: JSON ExplorationV2MapRequest; body <=65536 bytes. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2MapRequest`)
- Response schema: ExplorationV2MapDto (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2MapDto`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.maps.get`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v2/exploration/maps/{mapId}`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: Map ID; optional state_id. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2MapDto`)
- Response schema: ExplorationV2MapDto (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2MapDto`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.root`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v2/exploration`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: No body/query. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `root redirect`)
- Response schema: HTTP 308 to /capabilities. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `root redirect`)
- Source route: `frontend/src/app/api/trace/v2/exploration/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v2.vocabulary.get`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V2`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v2/exploration/vocabulary/{vocabularyId}`
- Implementation status: `IMPLEMENTED_VALIDATED_BASELINE`
- Request schema: Vocabulary ID; no body/query. (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2VocabularyDto`)
- Response schema: ExplorationV2VocabularyDto (`frontend/src/features/trace-v49/exploration-v2/types.ts`; `ExplorationV2VocabularyDto`)
- Source route: `frontend/src/app/api/trace/v2/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v2/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v2/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v2.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: No caller-selected sorting; governed deterministic order.
- Caching: Cache-Control: private, no-store.
- Loading state: Request or server render pending.
- Empty state: Endpoint-specific empty arrays are valid; no unresolved fallback is inserted.
- Partial state: No partial-response protocol.
- Error state: 400/404/409/413/503 fail closed; binary render capacity may return 503.
- Frontend use: Typed client support exists; no final mounted visual page or navigation is added by this integration.
- Limitations: A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620.
- Explicit nonclaims: Exactly 21 evidence-qualified generic pair associations are validated. No Open Inquiry record is mixed into v2. No causal, directional, hierarchical, temporal, equivalence, strength, pair-closure, higher-order-closure, computational-space, or Function 3 closure claim.

### `trace.f3.validated.v3.active.association-realizations.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/association-realizations/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3AssociationRealizationDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3AssociationRealizationDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.association-realizations.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/association-realizations`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3AssociationRealizationDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3AssociationRealizationDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.associations.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/associations/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3AssociationDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3AssociationDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.associations.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/associations`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3AssociationDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3AssociationDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.composition-coherence-reviews.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/composition-coherence-reviews/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3CompositionCoherenceReviewDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3CompositionCoherenceReviewDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.composition-coherence-reviews.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/composition-coherence-reviews`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3CompositionCoherenceReviewDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3CompositionCoherenceReviewDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.compositions.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/compositions/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3CompositionDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3CompositionDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.compositions.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/compositions`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3CompositionDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3CompositionDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.concept-senses.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/concept-senses/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3ConceptSenseDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ConceptSenseDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.concept-senses.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/concept-senses`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3ConceptSenseDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ConceptSenseDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.concepts.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/concepts/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3ConceptDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ConceptDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.concepts.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/concepts`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3ConceptDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ConceptDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.exports.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/exports/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3ExportDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ExportDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.exports.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/exports`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3ExportDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ExportDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.incidences.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/incidences/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3IncidenceDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3IncidenceDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.incidences.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/incidences`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3IncidenceDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3IncidenceDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.navigation-states.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/navigation-states/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3NavigationStateDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3NavigationStateDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.navigation-states.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/navigation-states`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3NavigationStateDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3NavigationStateDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.scopes.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/scopes/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3ScopeDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ScopeDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.scopes.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/scopes`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3ScopeDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ScopeDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.transitions.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/transitions/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3TransitionDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3TransitionDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.transitions.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/transitions`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3TransitionDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3TransitionDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.workflows.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/workflows/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3WorkflowDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3WorkflowDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.active.workflows.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/workflows`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3WorkflowDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3WorkflowDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.baseline-reconciliation.get`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/baseline/reconciliation`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 request`)
- Response schema: ExplorationV3ResponseEnvelope<{baseline_reconciliation}> (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ResponseEnvelope`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.capabilities.get`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ACTIVE`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/capabilities`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 request`)
- Response schema: ExplorationV3ResponseEnvelope<{capabilities,contract_version,source_authority}> (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ResponseEnvelope`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.association-realizations.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/association-realizations/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3AssociationRealizationDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3AssociationRealizationDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.association-realizations.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/association-realizations`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3AssociationRealizationDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3AssociationRealizationDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.associations.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/associations/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3AssociationDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3AssociationDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.associations.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/associations`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3AssociationDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3AssociationDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.composition-coherence-reviews.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/composition-coherence-reviews/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3CompositionCoherenceReviewDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3CompositionCoherenceReviewDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.composition-coherence-reviews.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/composition-coherence-reviews`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3CompositionCoherenceReviewDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3CompositionCoherenceReviewDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.compositions.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/compositions/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3CompositionDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3CompositionDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.compositions.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/compositions`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3CompositionDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3CompositionDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.concept-senses.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/concept-senses/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3ConceptSenseDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ConceptSenseDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.concept-senses.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/concept-senses`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3ConceptSenseDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ConceptSenseDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.concepts.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/concepts/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3ConceptDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ConceptDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.concepts.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/concepts`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3ConceptDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ConceptDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.exports.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/exports/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3ExportDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ExportDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.exports.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/exports`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3ExportDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ExportDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.incidences.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/incidences/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3IncidenceDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3IncidenceDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.incidences.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/incidences`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3IncidenceDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3IncidenceDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.navigation-states.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/navigation-states/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3NavigationStateDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3NavigationStateDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.navigation-states.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/navigation-states`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3NavigationStateDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3NavigationStateDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.scopes.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/scopes/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3ScopeDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ScopeDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.scopes.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/scopes`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3ScopeDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ScopeDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.transitions.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/transitions/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3TransitionDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3TransitionDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.transitions.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/transitions`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3TransitionDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3TransitionDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.workflows.detail`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/workflows/{id}`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: Path identifier, non-empty and <=512 characters; no body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-detail request`)
- Response schema: ExplorationV3ResponseEnvelope containing one ExplorationV3WorkflowDto and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3WorkflowDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.control.workflows.list`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_SYNTHETIC_CONTROL`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration/controls/workflows`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body; query currently ignored. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 collection-list request`)
- Response schema: ExplorationV3ResponseEnvelope list of ExplorationV3WorkflowDto records with collection, count, and data_class. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3WorkflowDto`)
- Source route: `frontend/src/app/api/trace/v3/exploration/[...path]/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

### `trace.f3.validated.v3.root`

- Function/layer: `TRACE_FUNCTION_3` / `VALIDATED_EXPLORATION_V3_ROOT`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v3/exploration`
- Implementation status: `IMPLEMENTED_FAIL_CLOSED_READ_ONLY`
- Request schema: No body/query. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3 request`)
- Response schema: HTTP 308 to /capabilities. (`frontend/src/features/trace-v49/exploration-v3/types.ts`; `ExplorationV3ResponseEnvelope`)
- Source route: `frontend/src/app/api/trace/v3/exploration/route.ts`
- Handler: `frontend/src/features/trace-v49/exploration-v3/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/exploration-v3/service.server.ts`
- Test: `frontend/scripts/test-trace-exploration-v3.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Fixed read-model order; no caller-selected sorting.
- Caching: Cache-Control: private, no-store.
- Loading state: Request pending.
- Empty state: Active-product collection lists are intentionally empty while activation remains fail closed.
- Partial state: No partial-response protocol.
- Error state: 404 invalid/not-active identifier; 405 unsupported method; 503 read-model integrity failure.
- Frontend use: Integrity and evidence infrastructure only; no mounted frontend consumes v3 in this integration.
- Limitations: Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS.
- Explicit nonclaims: Synthetic controls are not Open Inquiry records and are not active product facts. V3 does not inherit v2 transitions. V3 does not establish any closure claim.

## TRACE Function 3 — Open Inquiry

### `trace.f3.open-inquiry.v1.detail`

- Function/layer: `TRACE_FUNCTION_3` / `OPEN_INQUIRY`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v1/open-inquiry/{inquiryId}`
- Implementation status: `IMPLEMENTED_READ_ONLY_ISOLATED`
- Request schema: Exact R16B-HYPOTHESIS or R16B-SCOPED-HYPOTHESIS stable ID; no body or query. (`schemas/trace/exploration/open-inquiry/v1/detail-response.schema.json`; `OpenInquiry detail request`)
- Response schema: OpenInquiryResponseEnvelope<OpenInquiryDetailData>. (`schemas/trace/exploration/open-inquiry/v1/detail-response.schema.json`; `OpenInquiryDetailData`)
- Source route: `frontend/src/app/api/trace/v1/open-inquiry/[inquiryId]/route.ts`
- Handler: `frontend/src/features/trace-v49/open-inquiry-v1/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/open-inquiry-v1/service.server.ts`
- Test: `frontend/scripts/test-trace-open-inquiry-v1.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Canonical code-point order by stable inquiry ID; no caller-selected sort.
- Caching: Cache-Control: private, no-store; Vary: Accept; registry digest response header.
- Loading state: Request pending with Open Inquiry label retained.
- Empty state: List is governed at exactly 11; detail has no empty success state.
- Partial state: No partial-response protocol.
- Error state: 400 any query; 404 malformed/unknown ID; 405 unsupported method; 503 registry integrity failure.
- Frontend use: Future explicitly labelled inquiry inventory and detail surfaces; no visual design or mounted page is added here.
- Limitations: No pagination, filtering, caller sorting, randomization, mutation, or include-unresolved flag. External human review remains pending.
- Explicit nonclaims: Every record is unresolved and not validated. No record generates pair edges or changes validated graph, composition, topology, export, or metrics. No truth probability, likelihood score, confidence percentage, or stochastic display exists.

### `trace.f3.open-inquiry.v1.list`

- Function/layer: `TRACE_FUNCTION_3` / `OPEN_INQUIRY`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/trace/v1/open-inquiry`
- Implementation status: `IMPLEMENTED_READ_ONLY_ISOLATED`
- Request schema: No body and no query parameters. (`schemas/trace/exploration/open-inquiry/v1/list-response.schema.json`; `OpenInquiry list request`)
- Response schema: OpenInquiryResponseEnvelope<OpenInquiryListData> with exactly 11 items. (`schemas/trace/exploration/open-inquiry/v1/list-response.schema.json`; `OpenInquiryListData`)
- Source route: `frontend/src/app/api/trace/v1/open-inquiry/route.ts`
- Handler: `frontend/src/features/trace-v49/open-inquiry-v1/controller.server.ts`
- Service/repository: `frontend/src/features/trace-v49/open-inquiry-v1/service.server.ts`
- Test: `frontend/scripts/test-trace-open-inquiry-v1.mjs`
- Authentication: None.
- Pagination: None.
- Sorting: Canonical code-point order by stable inquiry ID; no caller-selected sort.
- Caching: Cache-Control: private, no-store; Vary: Accept; registry digest response header.
- Loading state: Request pending with Open Inquiry label retained.
- Empty state: List is governed at exactly 11; detail has no empty success state.
- Partial state: No partial-response protocol.
- Error state: 400 any query; 404 malformed/unknown ID; 405 unsupported method; 503 registry integrity failure.
- Frontend use: Future explicitly labelled inquiry inventory and detail surfaces; no visual design or mounted page is added here.
- Limitations: No pagination, filtering, caller sorting, randomization, mutation, or include-unresolved flag. External human review remains pending.
- Explicit nonclaims: Every record is unresolved and not validated. No record generates pair edges or changes validated graph, composition, topology, export, or metrics. No truth probability, likelihood score, confidence percentage, or stochastic display exists.

## shared TRACE infrastructure

### `trace.shared.read-v1.atlas`

- Function/layer: `SHARED_TRACE_INFRASTRUCTURE` / `LEGACY_TRACE_READ_PLATFORM`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/v1/releases/{release}/trace/atlas`
- Implementation status: `IMPLEMENTED_LEGACY_READ_PLATFORM`
- Request schema: No body/query. (`frontend/src/lib/read-platform/types.ts`; `Read API v1 request`)
- Response schema: Read API v1 envelope containing TraceAtlas; errors use the repository problem body. (`frontend/src/lib/read-platform/types.ts`; `TraceAtlas`)
- Source route: `frontend/src/app/api/v1/[...path]/route.ts`
- Handler: `frontend/src/lib/read-platform/server/read-api-controller.ts`
- Service/repository: `frontend/src/lib/read-platform/repository.ts`
- Test: `frontend/scripts/run-v49-api-read-contract-closure.mjs`
- Authentication: None; exact release integrity uses Archive-Research-Manifest-Sha256.
- Pagination: None.
- Sorting: Fixed repository order.
- Caching: Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.
- Loading state: Request pending.
- Empty state: Trace overview is currently zero/message; no partial state.
- Partial state: Trace overview is currently zero/message; no partial state.
- Error state: 400 invalid argument/cursor; 404 unavailable resource; 409 release mismatch; 503 repository unavailable.
- Frontend use: Legacy Evidence Atlas/read-platform compatibility; shared infrastructure is not a fourth TRACE function.
- Limitations: Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable.
- Explicit nonclaims: Legacy TRACE infrastructure is not Validated Exploration or Open Inquiry. Zero typed relations must not be conflated with the 21 validated generic pair associations.

### `trace.shared.read-v1.objects.list`

- Function/layer: `SHARED_TRACE_INFRASTRUCTURE` / `LEGACY_TRACE_READ_PLATFORM`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/v1/releases/{release}/trace/objects`
- Implementation status: `IMPLEMENTED_LEGACY_READ_PLATFORM`
- Request schema: Optional layer, first (default 50, 1..100), and after cursor. (`frontend/src/lib/read-platform/types.ts`; `Read API v1 request`)
- Response schema: Read API v1 envelope containing Page<TraceObjectSummary>; errors use the repository problem body. (`frontend/src/lib/read-platform/types.ts`; `Page<TraceObjectSummary>`)
- Source route: `frontend/src/app/api/v1/[...path]/route.ts`
- Handler: `frontend/src/lib/read-platform/server/read-api-controller.ts`
- Service/repository: `frontend/src/lib/read-platform/repository.ts`
- Test: `frontend/scripts/run-v49-api-read-contract-closure.mjs`
- Authentication: None; exact release integrity uses Archive-Research-Manifest-Sha256.
- Pagination: Keyset cursor pagination.
- Sorting: Fixed ID keyset order.
- Caching: Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.
- Loading state: Request pending.
- Empty state: Empty page is valid; hasNextPage/endCursor represents partial pagination.
- Partial state: Empty page is valid; hasNextPage/endCursor represents partial pagination.
- Error state: 400 invalid argument/cursor; 404 unavailable resource; 409 release mismatch; 503 repository unavailable.
- Frontend use: Legacy Evidence Atlas/read-platform compatibility; shared infrastructure is not a fourth TRACE function.
- Limitations: Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable.
- Explicit nonclaims: Legacy TRACE infrastructure is not Validated Exploration or Open Inquiry. Zero typed relations must not be conflated with the 21 validated generic pair associations.

### `trace.shared.read-v1.objects.neighborhood`

- Function/layer: `SHARED_TRACE_INFRASTRUCTURE` / `LEGACY_TRACE_READ_PLATFORM`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/v1/releases/{release}/trace/objects/{id}/neighborhood`
- Implementation status: `IMPLEMENTED_LEGACY_READ_PLATFORM`
- Request schema: Object ID; no body/query. (`frontend/src/lib/read-platform/types.ts`; `Read API v1 request`)
- Response schema: Read API v1 envelope containing TraceGraph; errors use the repository problem body. (`frontend/src/lib/read-platform/types.ts`; `TraceGraph`)
- Source route: `frontend/src/app/api/v1/[...path]/route.ts`
- Handler: `frontend/src/lib/read-platform/server/read-api-controller.ts`
- Service/repository: `frontend/src/lib/read-platform/repository.ts`
- Test: `frontend/scripts/run-v49-api-read-contract-closure.mjs`
- Authentication: None; exact release integrity uses Archive-Research-Manifest-Sha256.
- Pagination: None.
- Sorting: Fixed repository order.
- Caching: Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.
- Loading state: Request pending.
- Empty state: Current baseline returns 404/no nodes; no partial state.
- Partial state: Current baseline returns 404/no nodes; no partial state.
- Error state: 400 invalid argument/cursor; 404 unavailable resource; 409 release mismatch; 503 repository unavailable.
- Frontend use: Legacy Evidence Atlas/read-platform compatibility; shared infrastructure is not a fourth TRACE function.
- Limitations: Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable.
- Explicit nonclaims: Legacy TRACE infrastructure is not Validated Exploration or Open Inquiry. Zero typed relations must not be conflated with the 21 validated generic pair associations.

### `trace.shared.read-v1.relation-types.detail`

- Function/layer: `SHARED_TRACE_INFRASTRUCTURE` / `LEGACY_TRACE_READ_PLATFORM`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/v1/releases/{release}/trace/relation-types/{id}`
- Implementation status: `IMPLEMENTED_LEGACY_READ_PLATFORM`
- Request schema: Relation-type ID; no body/query. (`frontend/src/lib/read-platform/types.ts`; `Read API v1 request`)
- Response schema: Read API v1 envelope containing RelationTypeDefinition; errors use the repository problem body. (`frontend/src/lib/read-platform/types.ts`; `RelationTypeDefinition`)
- Source route: `frontend/src/app/api/v1/[...path]/route.ts`
- Handler: `frontend/src/lib/read-platform/server/read-api-controller.ts`
- Service/repository: `frontend/src/lib/read-platform/repository.ts`
- Test: `frontend/scripts/run-v49-api-read-contract-closure.mjs`
- Authentication: None; exact release integrity uses Archive-Research-Manifest-Sha256.
- Pagination: None.
- Sorting: None.
- Caching: Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.
- Loading state: Request pending.
- Empty state: Current baseline returns 404; no partial state.
- Partial state: Current baseline returns 404; no partial state.
- Error state: 400 invalid argument/cursor; 404 unavailable resource; 409 release mismatch; 503 repository unavailable.
- Frontend use: Legacy Evidence Atlas/read-platform compatibility; shared infrastructure is not a fourth TRACE function.
- Limitations: Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable.
- Explicit nonclaims: Legacy TRACE infrastructure is not Validated Exploration or Open Inquiry. Zero typed relations must not be conflated with the 21 validated generic pair associations.

### `trace.shared.read-v1.relation-types.list`

- Function/layer: `SHARED_TRACE_INFRASTRUCTURE` / `LEGACY_TRACE_READ_PLATFORM`
- Method: `GET, HEAD, OPTIONS`
- Route: `/api/v1/releases/{release}/trace/relation-types`
- Implementation status: `IMPLEMENTED_LEGACY_READ_PLATFORM`
- Request schema: No body/query. (`frontend/src/lib/read-platform/types.ts`; `Read API v1 request`)
- Response schema: Read API v1 envelope containing RelationTypeDefinition[]; errors use the repository problem body. (`frontend/src/lib/read-platform/types.ts`; `RelationTypeDefinition[]`)
- Source route: `frontend/src/app/api/v1/[...path]/route.ts`
- Handler: `frontend/src/lib/read-platform/server/read-api-controller.ts`
- Service/repository: `frontend/src/lib/read-platform/repository.ts`
- Test: `frontend/scripts/run-v49-api-read-contract-closure.mjs`
- Authentication: None; exact release integrity uses Archive-Research-Manifest-Sha256.
- Pagination: None.
- Sorting: Fixed repository order.
- Caching: Cache-Control: no-store; Vary: Archive-Research-Manifest-Sha256.
- Loading state: Request pending.
- Empty state: Current list is empty; no partial state.
- Partial state: Current list is empty; no partial state.
- Error state: 400 invalid argument/cursor; 404 unavailable resource; 409 release mismatch; 503 repository unavailable.
- Frontend use: Legacy Evidence Atlas/read-platform compatibility; shared infrastructure is not a fourth TRACE function.
- Limitations: Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable.
- Explicit nonclaims: Legacy TRACE infrastructure is not Validated Exploration or Open Inquiry. Zero typed relations must not be conflated with the 21 validated generic pair associations.

## Verification result

```text
IMPLEMENTED_TRACE_API_UNCATALOGUED_COUNT=0
CATALOG_IMPLEMENTED_WITHOUT_REAL_ROUTE_COUNT=0
CATALOG_DUPLICATE_METHOD_ROUTE_COUNT=0
CATALOG_SOURCE_PATH_MISSING_COUNT=0
CATALOG_TEST_PATH_MISSING_COUNT=0
```

Open Inquiry remains isolated from Validated Exploration. Synthetic v3 controls remain labelled synthetic controls, not Open Inquiry. No route in this catalog establishes pair, higher-order, global-composition, product-reachability, computational-space, or Function 3 closure.
