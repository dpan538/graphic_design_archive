# Frontend functional architecture and scale census

> Source: `4fbb3d559a98614e8cd94656a8871db18ee06f3c`. This is the authoritative functional handoff for later frontend design—not visual design, API-schema invention, research closure, or deployment. The machine-readable equivalent is `product-functional-census.v1.json`.

## 1. Executive summary

Graphic Design Archive has two parallel product strategies: Global Search and TRACE. Search is the mobile-capable public-object entry. TRACE has exactly three desktop research functions: Context Canvas, Spacetime, and Exploration; Exploration keeps Validated Exploration and Open Inquiry separate. System Suggestions is optional orientation, never evidence or a core dependency.

| Measure | Exact value |
|---|---:|
| Product areas | 3 |
| Active public product route templates | 5 |
| Final design screens | 7 |
| Reference or legacy screens | 6 |
| User-facing product functions | 13 |
| User actions | 47 |
| Functional zones | 16 |
| Public Search documents | 7995 |
| API route templates / method pairs | 91 / 275 |

## 2. Source/release identity

| Field | Value |
|---|---|
| Repository | dpan538/graphic_design_archive |
| Source SHA | `4fbb3d559a98614e8cd94656a8871db18ee06f3c` |
| Source tree SHA | `7307745b7844035784ad1ab6906837d874b164fb` |
| Database version | 50 |
| Database freeze hash | `f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e` |
| Release | v49-api-contract-fresh-c |
| Frontend build version | 0.1.0 |

## 3. Product hierarchy

```text
Graphic Design Archive
├── Global Search (homepage, desktop, mobile, object detail)
└── TRACE (desktop research environment)
    ├── Context Canvas
    ├── Spacetime
    └── Exploration
        ├── Validated Exploration
        └── Open Inquiry
```

`TRACE_TOP_LEVEL_FUNCTION_COUNT=3`
`GLOBAL_SEARCH_IS_TRACE_CHILD=false`
`GLOBAL_SEARCH_MOBILE_AVAILABLE=true`
`TRACE_FULL_MOBILE_RUNTIME_ENABLED=false`
`SYSTEM_SUGGESTIONS_IS_PRODUCT_GUIDANCE_NOT_CORE_EVIDENCE=true`

## 4. Active screen and route census

| Route | Classification | Platform | Functional zones | Claude designs | Reason |
|---|---|---|---|---|---|
| `/about` | ACTIVE_PUBLIC_PRODUCT | DESKTOP_AND_MOBILE | zone.about-methodology | yes | Required shared product information route. |
| `/appendix` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/badges` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/bookmarks/horizontal` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/bookmarks` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/bookmarks/vertical` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/cards/color` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/cards/dense` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/cards` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/cards/rectangle` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/cards/special` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/cards/square` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/contents` | DOCUMENTATION_OR_METHOD | DESKTOP_AND_MOBILE | zone.about-methodology | no | Documentation supports methodology but is not a final product screen. |
| `/folders/{type}/{slug}` | LEGACY_PUBLIC | DESKTOP_AND_MOBILE | — | no | Legacy read-platform surface; final IA is Search-first. |
| `/folders/{type}` | LEGACY_PUBLIC | DESKTOP_AND_MOBILE | — | no | Legacy read-platform surface; final IA is Search-first. |
| `/folders` | LEGACY_PUBLIC | DESKTOP_AND_MOBILE | — | no | Legacy read-platform surface; final IA is Search-first. |
| `/main-sheets` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/` | ACTIVE_PUBLIC_PRODUCT | DESKTOP_AND_MOBILE | zone.home, zone.global-navigation | yes | Current homepage is the canonical product entry. |
| `/reading-notes` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/search` | ACTIVE_PUBLIC_PRODUCT | DESKTOP_AND_MOBILE | zone.search, zone.search-filters, zone.search-results, zone.search-pagination, zone.system-suggestions | yes | Current functional Search implementation. |
| `/slips` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/sub-sheets` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/surfaces/{id}` | ACTIVE_PUBLIC_PRODUCT | DESKTOP_AND_MOBILE | zone.object-detail | yes | Search target route; current detail UI remains metadata/citation only. |
| `/text-pages` | INTERNAL_TEST_OR_DEMO | NOT_USER_FACING | — | no | Asset study only. |
| `/trace/context-canvas` | ACTIVE_REFERENCE_IMPLEMENTATION | MOBILE_LIGHTWEIGHT_FALLBACK | zone.context-canvas, zone.system-suggestions, zone.trace-exports | yes | Functional unlinked reference workspace to design for final TRACE IA. |
| `/trace` | ACTIVE_PUBLIC_PRODUCT | MOBILE_LIGHTWEIGHT_FALLBACK | zone.trace-entry, zone.validated-exploration, zone.open-inquiry | yes | Top-level TRACE entry; full mobile runtime is intentionally disabled. |
| `/trace/spacetime` | ACTIVE_REFERENCE_IMPLEMENTATION | MOBILE_LIGHTWEIGHT_FALLBACK | zone.spacetime, zone.system-suggestions | yes | Functional unlinked reference workspace to design for final TRACE IA. |
| `/trace/types/{type}` | ACTIVE_REFERENCE_IMPLEMENTATION | DESKTOP_ONLY | — | no | Historical/reference route; not one of the three final TRACE functions. |

The direct Context Canvas and Spacetime paths are functional, no-index reference workspaces. They are final-design candidates but are not evidence that their current navigation or visual treatment is final. The 8,636-record `public_surface_mock_v0` is explicitly non-final static legacy data and is not used for public product scale.

## 5. Functional-zone census

| Zone | Purpose | Platform | Required APIs | Readiness |
|---|---|---|---|---|
| zone.home | Homepage Search entry | DESKTOP_AND_MOBILE | search.facets.v1 | FUNCTIONALLY_READY |
| zone.global-navigation | Global navigation | DESKTOP_AND_MOBILE | — | BACKEND_READY_FRONTEND_NOT_DESIGNED |
| zone.search | Global Search workspace | DESKTOP_AND_MOBILE | search.public-objects.v1, search.facets.v1 | FUNCTIONALLY_READY |
| zone.search-filters | Search filters | DESKTOP_AND_MOBILE | search.public-objects.v1, search.facets.v1 | FUNCTIONALLY_READY |
| zone.search-results | Search result cards | DESKTOP_AND_MOBILE | search.public-objects.v1 | FUNCTIONALLY_READY |
| zone.search-pagination | Search pagination | DESKTOP_AND_MOBILE | search.public-objects.v1 | FUNCTIONALLY_READY |
| zone.object-detail | Object Detail | DESKTOP_AND_MOBILE | read.surface-detail.v1 | BACKEND_READY_FRONTEND_NOT_DESIGNED |
| zone.about-methodology | About / Methodology | DESKTOP_AND_MOBILE | — | BACKEND_READY_FRONTEND_NOT_DESIGNED |
| zone.trace-entry | TRACE entry / Exploration | MOBILE_LIGHTWEIGHT_FALLBACK | trace.f3.validated.v2.capabilities.get, trace.f3.open-inquiry.v1.list | BACKEND_READY_FRONTEND_NOT_DESIGNED |
| zone.context-canvas | Context Canvas | MOBILE_LIGHTWEIGHT_FALLBACK | trace.f1.context.object-context.v1 | FUNCTIONALLY_READY |
| zone.spacetime | Spacetime | MOBILE_LIGHTWEIGHT_FALLBACK | trace.f2.spacetime.periods.v1, trace.f2.spacetime.atlas.v1, trace.f2.spacetime.geography-records.v1 | FUNCTIONALLY_READY |
| zone.validated-exploration | Validated Exploration | MOBILE_LIGHTWEIGHT_FALLBACK | trace.f3.validated.v2.capabilities.get, trace.f3.validated.v2.categories.list, trace.f3.validated.v2.maps.create, trace.f3.validated.v2.maps.get, trace.f3.validated.v2.maps.actions, trace.f3.validated.v2.vocabulary.get, trace.f3.validated.v2.associations.get | FUNCTIONALLY_READY |
| zone.open-inquiry | Open Inquiry | MOBILE_LIGHTWEIGHT_FALLBACK | trace.f3.open-inquiry.v1.list, trace.f3.open-inquiry.v1.detail | BACKEND_READY_FRONTEND_NOT_DESIGNED |
| zone.trace-exports | TRACE exports | DESKTOP_ONLY | trace.f3.validated.v2.exports.manifest, trace.f3.validated.v2.exports.png, trace.f3.validated.v2.exports.svg | FUNCTIONALLY_READY |
| zone.system-suggestions | System Suggestions | DESKTOP_AND_MOBILE | guidance.system-suggestions.v1 | FUNCTIONALLY_READY |
| zone.shared-states | Shared loading, empty, partial, and error states | DESKTOP_AND_MOBILE | — | BACKEND_READY_FRONTEND_NOT_DESIGNED |

## 6. Global Search specification

Search has one deterministic relevance order over exactly 7995 public documents. Text fields are stable ID, title, credited label, and place. Hard conjunctive filters are year, object type, theme, and movement. The client uses a 25-result default page and a 50-result API maximum; URL state preserves query, filters, and cursor. Search result DTOs have no image URL or thumbnail field.

## 7. Object Detail specification

`/surfaces/{id}` is the Search target route. Current rendering is public metadata plus a permitted citation when available; it does not render an image. A future design must preserve Search history and must not assume a visual asset from object metadata or delivery-state labels.

## 8. TRACE overview

TRACE is intentionally desktop-first. A likely mobile request returns the lightweight desktop-required state before governed runtime imports and links back to Search. No route, API version, export type, or V3 research-control collection creates a fourth TRACE function.

## 9. Context Canvas specification

Context Canvas covers 7995 public objects with 16106 governed representations across 25 controlled terms. It is project-curated context, never a historical relation. Design both spatial canvas and synchronized accessible rows; preserve explicit provenance and the browser PNG export limits.

## 10. Spacetime specification

Spacetime has 23 decade periods, 93 governed geographies, and 373 non-zero aggregate cells. A map mark is aggregate recorded context, not an object coordinate, movement path, influence relation, or association. The accessible geography table is an equivalent representation.

## 11. Validated Exploration specification

The functional product contract is V2: 31 vocabulary entries, 21 evidence-qualified generic pair associations, 5,760 governed states, 749,944 transitions, and 11,520 export variants. The server owns state hashes, available actions, tree, and export identity. V3 exposes fail-closed read/reconciliation resources with zero production activations; do not design V3 controls as user product screens.

## 12. Open Inquiry specification

Open Inquiry contains exactly 11 scoped unresolved records. Its persistent order is: **Open inquiry**; **Evidence remains incomplete.**; **This is not a validated historical association.**; then optional System Suggestions. It cannot enter validated graph, composition, topology, export, or metrics; no confidence scale, probability, or stochastic ordering is permitted.

## 13. System Suggestions specification

| Rule | Current contract |
|---|---|
| Public label | System suggests |
| Surfaces | SEARCH_RESULTS, TRACE_CONTEXT, TRACE_SPACETIME, TRACE_VALIDATED_EXPLORATION, TRACE_OPEN_INQUIRY |
| Provider optional / core dependent | true / false |
| Ordinary UI provider disclosure | none |
| About/Methodology disclosure | yes |
| States | guidance_loading, model_guidance_available, static_fallback_guidance, guidance_hidden_after_transport_failure, no_allowed_suggestion, rate_limited |
| Maximum request / note / suggestions | 16,384 bytes / 320 code points / 4 |

Provider output is only a validated candidate selection plus a bounded note. Search result objects, held records, raw evidence, and provider identity are outside the ordinary UI and request boundary.

## 14. Navigation and user flows

| Source | Action | Destination | URL | State preservation | API |
|---|---|---|---|---|---|
| zone.home | submit Search or choose starter | zone.search | /search?… | URL state begins | search.facets.v1 |
| zone.search-results | open result | zone.object-detail | /surfaces/{id} | Search URL retained in history | read.surface-detail.v1 |
| zone.home | enter TRACE | zone.trace-entry | /trace | none | trace.f3.validated.v2.capabilities.get |
| zone.trace-entry | open Context Canvas | zone.context-canvas | /trace/context-canvas | record parameter | trace.f1.context.object-context.v1 |
| zone.trace-entry | open Spacetime | zone.spacetime | /trace/spacetime | period/geography state | trace.f2.spacetime.periods.v1 |
| zone.validated-exploration | read separate Open Inquiry | zone.open-inquiry | same TRACE route/layer | validated state is not copied | trace.f3.open-inquiry.v1.list |
| zone.system-suggestions | explicitly select approved suggestion | zone.search | /search?… | changes URL only after click | guidance.system-suggestions.v1 |
| zone.validated-exploration | request export | zone.trace-exports | no navigation | bind map/state/hash | trace.f3.validated.v2.exports.manifest |

## 15. Desktop/mobile matrix

| Zone | Policy | Product meaning |
|---|---|---|
| zone.home | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |
| zone.global-navigation | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |
| zone.search | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |
| zone.search-filters | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |
| zone.search-results | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |
| zone.search-pagination | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |
| zone.object-detail | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |
| zone.about-methodology | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |
| zone.trace-entry | MOBILE_LIGHTWEIGHT_FALLBACK | Mobile returns the intentional desktop-required state and Search option. |
| zone.context-canvas | MOBILE_LIGHTWEIGHT_FALLBACK | Mobile returns the intentional desktop-required state and Search option. |
| zone.spacetime | MOBILE_LIGHTWEIGHT_FALLBACK | Mobile returns the intentional desktop-required state and Search option. |
| zone.validated-exploration | MOBILE_LIGHTWEIGHT_FALLBACK | Mobile returns the intentional desktop-required state and Search option. |
| zone.open-inquiry | MOBILE_LIGHTWEIGHT_FALLBACK | Mobile returns the intentional desktop-required state and Search option. |
| zone.trace-exports | DESKTOP_ONLY | Reflow ordinary reading and controls without semantic loss. |
| zone.system-suggestions | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |
| zone.shared-states | DESKTOP_AND_MOBILE | Reflow ordinary reading and controls without semantic loss. |

`SEARCH_CLIENT_BUNDLE_TRACE_IMPORT_COUNT=0`. Desktop-only TRACE is intentional product policy, not a responsive defect.

## 16. Frontend-required API table

Only these 19 `FRONTEND_REQUIRED_NOW` routes belong in a final frontend implementation now.

| API ID | Method and route | Purpose |
|---|---|---|
| search.public-objects.v1 | `GET, HEAD, OPTIONS /api/search/v1` | Public result DTOs, exact count, bounded page info, aggregate summaries, release/checksum identity, plain-language explanation, and audit-only scoring metadata. |
| search.facets.v1 | `GET, HEAD, OPTIONS /api/search/v1/facets` | Release-bound year limits, 90 object types, 8 themes, 7 movements, counts, document total, and four deterministic starter queries. |
| trace.f3.open-inquiry.v1.list | `GET, HEAD, OPTIONS /api/trace/v1/open-inquiry` | OpenInquiryResponseEnvelope<OpenInquiryListData> with exactly 11 items. |
| trace.f3.open-inquiry.v1.detail | `GET, HEAD, OPTIONS /api/trace/v1/open-inquiry/{inquiryId}` | OpenInquiryResponseEnvelope<OpenInquiryDetailData>. |
| trace.f3.validated.v2.associations.get | `GET, HEAD, OPTIONS /api/trace/v2/exploration/associations/{associationId}` | ExplorationV2AssociationDto |
| trace.f3.validated.v2.capabilities.get | `GET, HEAD, OPTIONS /api/trace/v2/exploration/capabilities` | ExplorationV2CapabilitiesResponse |
| trace.f3.validated.v2.categories.list | `GET, HEAD, OPTIONS /api/trace/v2/exploration/categories` | ExplorationV2CategoriesResponse |
| trace.f3.validated.v2.exports.svg | `POST, OPTIONS /api/trace/v2/exploration/export/svg` | image/svg+xml bytes with semantic/presentation/state/export headers |
| trace.f3.validated.v2.exports.manifest | `POST, OPTIONS /api/trace/v2/exploration/exports/manifest` | ExplorationV2ExportManifestDto |
| trace.f3.validated.v2.exports.png | `POST, OPTIONS /api/trace/v2/exploration/exports/png` | image/png bytes with semantic/presentation/state/export headers |
| trace.f3.validated.v2.maps.create | `POST, OPTIONS /api/trace/v2/exploration/maps` | ExplorationV2MapDto |
| trace.f3.validated.v2.maps.get | `GET, HEAD, OPTIONS /api/trace/v2/exploration/maps/{mapId}` | ExplorationV2MapDto |
| trace.f3.validated.v2.maps.actions | `POST, OPTIONS /api/trace/v2/exploration/maps/{mapId}/actions` | ExplorationV2MapDto |
| trace.f3.validated.v2.vocabulary.get | `GET, HEAD, OPTIONS /api/trace/v2/exploration/vocabulary/{vocabularyId}` | ExplorationV2VocabularyDto |
| read.surface-detail.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/surfaces/{surfaceId}` | One public object detail used by Search result routes. |
| trace.f1.context.object-context.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/trace/objects/{id}/context` | Read API v1 envelope containing PublicContextDataset. |
| trace.f2.spacetime.atlas.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/trace/spacetime/atlas` | Read API v1 envelope containing PublicSpacetimeAtlasDataset. |
| trace.f2.spacetime.geography-records.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/trace/spacetime/geographies/{geographyId}/records` | Read API v1 envelope containing PublicSpacetimeRecordPage. |
| trace.f2.spacetime.periods.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/trace/spacetime/periods` | Read API v1 envelope containing PublicSpacetimePeriodsDataset. |

`guidance.system-suggestions.v1` is the single `FRONTEND_OPTIONAL` API: it may enhance a loaded screen but must never gate it.

## 17. Complete API classification appendix

The canonical complete map remains [PRODUCT_API_MAP.md](../../api/PRODUCT_API_MAP.md). This appendix adds frontend-consumption disposition; it does not replace request/response schemas.

### FRONTEND_OPTIONAL

| API ID | Route | Reason |
|---|---|---|
| guidance.system-suggestions.v1 | `POST, OPTIONS /api/system-suggestions/v1` | In-memory rate protection is process-local; guidance is non-persistent and optional. |

### SERVER_SIDE_SUPPORT

| API ID | Route | Reason |
|---|---|---|
| trace.f3.validated.v2.root | `GET, HEAD, OPTIONS /api/trace/v2/exploration` | A map exposes at most eight visible nodes. Map GET recognizes state_id; other query keys are currently ignored. PNG is fixed at 1080×1620. |
| read.release.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}` | No public release listing endpoint. |
| read.archive-overview.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/archive/overview` | Selected release only. |
| read.release-manifest.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/manifest` | Manifest response is the compact repository version envelope. |

### INTERNAL_RESEARCH_CONTROL

| API ID | Route | Reason |
|---|---|---|
| trace.f3.validated.v3.control.association-realizations.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/association-realizations` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.association-realizations.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/association-realizations/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.associations.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/associations` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.associations.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/associations/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.composition-coherence-reviews.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/composition-coherence-reviews` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.composition-coherence-reviews.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/composition-coherence-reviews/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.compositions.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/compositions` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.compositions.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/compositions/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.concept-senses.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/concept-senses` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.concept-senses.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/concept-senses/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.concepts.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/concepts` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.concepts.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/concepts/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.exports.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/exports` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.exports.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/exports/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.incidences.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/incidences` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.incidences.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/incidences/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.navigation-states.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/navigation-states` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.navigation-states.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/navigation-states/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.scopes.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/scopes` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.scopes.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/scopes/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.transitions.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/transitions` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.transitions.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/transitions/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.workflows.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/workflows` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.control.workflows.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/controls/workflows/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |

### LEGACY_COMPATIBILITY

| API ID | Route | Reason |
|---|---|---|
| read.claim-detail.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/claims/{claimId}` | No claim is generated at request time. |
| read.corpus-detail.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/corpora/{corpusVersion}` | No unrestricted corpus payload. |
| read.folder-types.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/folder-types` | No caller-selected order. |
| read.folders.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/folders` | Repository-standard cursor pagination. |
| read.folder-detail.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/folders/{folderId}` | Unknown folder returns 404. |
| read.folder-members.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/folders/{folderId}/surfaces` | Public membership projection only. |
| read.relation-detail.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/relations/{relationId}` | No relation is inferred at request time. |
| read.legacy-search.v1 | `GET, HEAD, OPTIONS /api/v1/releases/{release}/search` | Frozen v1 title/ID contract; Global Search v2 is /api/search/v1. |
| trace.shared.read-v1.atlas | `GET, HEAD, OPTIONS /api/v1/releases/{release}/trace/atlas` | Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable. |
| trace.shared.read-v1.objects.list | `GET, HEAD, OPTIONS /api/v1/releases/{release}/trace/objects` | Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable. |
| trace.shared.read-v1.objects.neighborhood | `GET, HEAD, OPTIONS /api/v1/releases/{release}/trace/objects/{id}/neighborhood` | Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable. |
| trace.shared.read-v1.relation-types.list | `GET, HEAD, OPTIONS /api/v1/releases/{release}/trace/relation-types` | Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable. |
| trace.shared.read-v1.relation-types.detail | `GET, HEAD, OPTIONS /api/v1/releases/{release}/trace/relation-types/{id}` | Neighborhood and relation-type detail dispatch currently tolerate trailing path segments; only canonical templates are cataloged. Current relation and neighborhood baselines are empty or unavailable. |

### RETIRED

| API ID | Route | Reason |
|---|---|---|
| trace.f3.validated.v1.retired-root | `GET, HEAD, OPTIONS, POST, PUT, PATCH, DELETE /api/trace/v1/exploration` | OPTIONS intentionally returns the retirement payload rather than 204. No v1 data remains available. |
| trace.f3.validated.v1.retired-catchall | `GET, HEAD, OPTIONS, POST, PUT, PATCH, DELETE /api/trace/v1/exploration/{...path}` | OPTIONS intentionally returns the retirement payload rather than 204. No v1 data remains available. |

### FAIL_CLOSED

| API ID | Route | Reason |
|---|---|---|
| trace.f3.validated.v3.root | `GET, HEAD, OPTIONS /api/trace/v3/exploration` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.association-realizations.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/association-realizations` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.association-realizations.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/association-realizations/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.associations.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/associations` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.associations.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/associations/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.baseline-reconciliation.get | `GET, HEAD, OPTIONS /api/trace/v3/exploration/baseline/reconciliation` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.capabilities.get | `GET, HEAD, OPTIONS /api/trace/v3/exploration/capabilities` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.composition-coherence-reviews.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/composition-coherence-reviews` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.composition-coherence-reviews.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/composition-coherence-reviews/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.compositions.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/compositions` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.compositions.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/compositions/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.concept-senses.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/concept-senses` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.concept-senses.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/concept-senses/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.concepts.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/concepts` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.concepts.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/concepts/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.exports.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/exports` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.exports.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/exports/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.incidences.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/incidences` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.incidences.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/incidences/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.navigation-states.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/navigation-states` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.navigation-states.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/navigation-states/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.scopes.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/scopes` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.scopes.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/scopes/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.transitions.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/transitions` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.transitions.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/transitions/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.workflows.list | `GET, HEAD, OPTIONS /api/trace/v3/exploration/workflows` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| trace.f3.validated.v3.active.workflows.detail | `GET, HEAD, OPTIONS /api/trace/v3/exploration/workflows/{id}` | Query parameters are currently ignored. Identifiers are non-empty and limited to 512 characters. Active-product lists are empty under FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS. |
| read.visual-registry-current.v1 | `GET, HEAD, OPTIONS /api/v1/visual-registries/current` | No visual registry is selected. |

## 18. Quantitative scale census

| Metric | Value | Source | Frontend significance / caveat |
|---|---:|---|---|
| archive.canonical_object_count | 15923 objects | `docs/statistics/v49-release-data-profile.json` | Separates corpus scale from public Search scale. |
| archive.active_public_object_count | 7995 objects | `docs/statistics/v49-release-data-profile.json` | Defines public product denominator. |
| archive.held_object_count | 7928 objects | `docs/statistics/v49-release-data-profile.json` | Never design a held-record UI state as public data. |
| archive.assignment_count | 47982 assignments | `docs/statistics/v49-release-data-profile.json` | Research-scale context only. |
| archive.positive_visual_rights_count | 0 records | `docs/statistics/v49-release-data-profile.json` | Search delivery-state labels are not a positive-rights grant. |
| search.public_document_count | 7995 documents | `frontend/generated/search-v2/manifest.json` | Primary Search scale. |
| search.held_document_count | 0 documents | `frontend/generated/search-v2/manifest.json` | Must remain zero. |
| search.trace_document_count | 0 documents | `frontend/generated/search-v2/manifest.json` | Must remain zero. |
| search.open_inquiry_document_count | 0 documents | `frontend/generated/search-v2/manifest.json` | Must remain zero. |
| search.index_bytes | 1890418 bytes | `frontend/generated/search-v2/manifest.json` | Server-only artifact size. |
| search.index_gzip_bytes | 272520 bytes | `frontend/generated/search-v2/manifest.json` | Server-only artifact size. |
| search.object_type_dictionary | 90 values | `frontend/generated/search-v2/facets.json` | Filter-control scale. |
| search.theme_dictionary | 8 values | `frontend/generated/search-v2/facets.json` | Filter-control scale. |
| search.movement_dictionary | 7 values | `frontend/generated/search-v2/facets.json` | Movement is sparse and never inferred. |
| search.remote_image_delivery_state_count | 155 documents | `frontend/generated/search-v2/documents.json` | Not a thumbnail or positive-rights authorization; Search DTO carries no image URL. |
| context.public_object_coverage | 7995 objects | `frontend/generated/trace-context-v1/manifest.json` | Context Canvas denominator. |
| context.representation_count | 16106 representations | `frontend/generated/trace-context-v1/manifest.json` | Context Canvas scale, not association count. |
| context.term_count | 25 terms | `frontend/generated/trace-context-v1/manifest.json` | Control vocabulary scale. |
| context.template_count | 3 templates | `frontend/src/features/trace-v49/context/canvas/templates.ts` | Design must support selectable governed composition templates. |
| spacetime.public_denominator | 7995 objects | `frontend/generated/trace-spacetime-v1/manifest.json` | Spacetime denominator. |
| spacetime.period_count | 23 periods | `frontend/generated/trace-spacetime-v1/manifest.json` | Period-control scale. |
| spacetime.geography_count | 93 geographies | `frontend/generated/trace-spacetime-v1/manifest.json` | Map/table selection scale. |
| spacetime.region_assignment_count | 7996 assignments | `frontend/generated/trace-spacetime-v1/manifest.json` | Do not confuse with period membership. |
| spacetime.map_cell_count | 373 cells | `frontend/generated/trace-spacetime-v1/manifest.json` | Aggregate map scale. |
| exploration.validated_association_count | 21 associations | `frontend/generated/trace-exploration-v2/production-read-model.json` | Do not imply causal or directional claims. |
| exploration.v2_reachable_state_count | 5760 states | `frontend/generated/trace-exploration-v2/production-read-model.json` | State-machine scale; not active V3 product facts. |
| exploration.v2_transition_count | 749944 transitions | `frontend/generated/trace-exploration-v2/production-read-model.json` | Server owns transitions. |
| exploration.v2_export_variant_count | 11520 variants | `frontend/generated/trace-exploration-v2/production-read-model.json` | Only current V2 export contract applies. |
| exploration.v3_active_product_activation_count | 0 activations | `frontend/generated/trace-exploration-v3/read-model.json` | Zero; V3 is fail-closed, not a screen requirement. |
| open_inquiry.count | 11 records | `frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json` | Inventory count only; not a likelihood or closure metric. |
| guidance.surface_count | 5 surfaces | `frontend/src/features/system-suggestions/types.ts` | One secondary component must work across five surfaces. |
| guidance.maximum_request_bytes | 16384 bytes | `frontend/src/features/system-suggestions/schema.server.ts` | Frontend sends only a bounded public summary. |
| guidance.maximum_note_length | 320 code points | `frontend/src/features/system-suggestions/service.server.ts` | Keep visual treatment compact and secondary. |
| guidance.maximum_suggestions | 4 suggestions | `frontend/src/features/system-suggestions/service.server.ts` | No arbitrary provider actions. |
| frontend.page_route_template_count | 28 routes | `frontend/src/app/page.tsx` | Includes legacy and internal routes; not a product feature count. |
| frontend.active_product_route_count | 5 routes | `frontend/src/app/page.tsx` | Final navigation candidate baseline. |
| frontend.active_product_screen_count | 7 screens | `frontend/scripts/generate-product-functional-census.mjs` | Final visual design scope, including two functional TRACE reference workspaces. |
| frontend.user_facing_function_count | 13 functions | `frontend/scripts/generate-product-functional-census.mjs` | Product capability scope rather than JavaScript function count. |
| frontend.user_action_count | 47 actions | `frontend/scripts/generate-product-functional-census.mjs` | Interaction inventory; not feature count. |
| frontend.functional_zone_count | 16 zones | `frontend/scripts/generate-product-functional-census.mjs` | Finite design scope. |
| api.route_template_count | 91 routes | `docs/api/product-api-map.v1.json` | Only classified frontend subset belongs in design. |
| api.method_route_pair_count | 275 method-route pairs | `docs/api/product-api-map.v1.json` | Validation metric, not a screen count. |

All test figures are **VALIDATION_METRIC_NOT_PRODUCT_FEATURE**. The release profile is authoritative for canonical/held/rights counts; the Search and governed artifacts are authoritative for product projection scale.

## 19. Rights and visual-material boundary

| Screen/state | Allowed material now |
|---|---|
| Homepage / Search controls | NO_VISUAL_ASSUMPTION_ALLOWED |
| Search result cards | TEXT_CITATION_ONLY; permitted thumbnail count is 0 |
| Object Detail | TEXT_CITATION_ONLY; current route renders no image |
| Context Canvas / Spacetime / Validated Exploration export | GENERATED_DIAGRAM_ONLY |
| Open Inquiry | TEXT_CITATION_ONLY |
| Legacy asset studies | REFERENCE_ONLY; never import their image policies into final product |

The sealed release profile reports positive visual rights count **0**. The Search artifact’s 155 `REMOTE_IMAGE` delivery labels are not positive-rights grants and do not include URLs in the Search DTO. Exports must not include third-party images; TRACE exports are internally rendered diagrams/text only. Decorative placeholder imagery is not authorized.

## 20. Export capabilities

| Capability | Format | Status | Boundary |
|---|---|---|---|
| export.context.png | PNG | IMPLEMENTED_BROWSER | Current governed Canvas composition and public-safe footer only. |
| export.spacetime.functional | canonical functional value | IMPLEMENTED_PREPARATION_NO_DOWNLOAD_ROUTE | Aggregate positions only; not object coordinates; no invented binary route. |
| export.validated.manifest | JSON | IMPLEMENTED | Exact V2 map/state/composition identity. |
| export.validated.png | PNG | IMPLEMENTED | Validated V2 diagram/text only; no third-party object image or Open Inquiry data. |
| export.validated.svg | SVG | IMPLEMENTED | Validated V2 diagram/text only; no third-party object image or Open Inquiry data. |

## 21. Shared states and accessibility

Every active zone has loading, valid empty/zero, partial only where contractual, safe error, and explicit retry behavior. All controls are keyboard-operable. Context Canvas exposes accessible rows; Spacetime exposes an equivalent table; Validated Exploration exposes the server-provided tree; Open Inquiry makes unresolved status textual and persistent. Never use colour, map geometry, or model guidance as the sole carrier of meaning.

## 22. Legacy/internal/retired surfaces

| Path | Classification | Why retained | Visible navigation | Claude designs | Component reuse |
|---|---|---|---|---|---|
| `/appendix` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/badges` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/bookmarks/horizontal` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/bookmarks` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/bookmarks/vertical` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/cards/color` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/cards/dense` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/cards` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/cards/rectangle` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/cards/special` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/cards/square` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/folders/{type}/{slug}` | LEGACY_PUBLIC | Legacy read-platform surface; final IA is Search-first. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/folders/{type}` | LEGACY_PUBLIC | Legacy read-platform surface; final IA is Search-first. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/folders` | LEGACY_PUBLIC | Legacy read-platform surface; final IA is Search-first. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/main-sheets` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/reading-notes` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/slips` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/sub-sheets` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |
| `/text-pages` | INTERNAL_TEST_OR_DEMO | Asset study only. | no | no | Only if reused without importing legacy data or visual-rights assumptions. |

## 23. Frontend readiness matrix

| Zone | Backend | API | Reference UI | Final UI designed | Mobile | Export | Blocker |
|---|---|---|---|---|---|---|---|
| zone.home | true | true | false | false | true | false | None |
| zone.global-navigation | true | false | false | false | true | false | None |
| zone.search | true | true | false | false | true | false | None |
| zone.search-filters | true | true | false | false | true | false | None |
| zone.search-results | true | true | false | false | true | false | None |
| zone.search-pagination | true | true | false | false | true | false | None |
| zone.object-detail | true | true | false | false | true | false | None |
| zone.about-methodology | true | true | false | false | true | false | None |
| zone.trace-entry | true | true | false | false | false | false | None |
| zone.context-canvas | true | true | true | false | false | true | None |
| zone.spacetime | true | true | true | false | false | false | None |
| zone.validated-exploration | true | true | true | false | false | false | V3 active production activation count is zero; do not invent a V3 active product screen. |
| zone.open-inquiry | true | true | true | false | false | false | None |
| zone.trace-exports | true | true | false | false | false | true | None |
| zone.system-suggestions | true | true | false | false | true | false | None |
| zone.shared-states | true | false | false | false | true | false | None |

## 24. Frontend design brief for Claude

### A. Exact product hierarchy

Design Global Search and TRACE as parallel homepage-level strategies. TRACE has exactly Context Canvas, Spacetime, and Exploration; Exploration contains separate Validated Exploration and Open Inquiry layers.

### B. Exact finite screen / functional-zone list to design

1. Homepage Search entry (desktop/mobile; Search form, starters, TRACE entry; text/citation-only).
2. Global Search (desktop/mobile; query, four filters, results, cursor, optional guidance; text/citation-only).
3. Object Detail (desktop/mobile; public metadata and permitted citation; no assumed image).
4. About / Methodology (desktop/mobile; methods and provider disclosure).
5. TRACE entry / Exploration (desktop plus mobile lightweight fallback; validated and Open Inquiry separation).
6. Context Canvas (desktop plus mobile lightweight fallback; canvas, rows, provenance, export).
7. Spacetime (desktop plus mobile lightweight fallback; period/geography/map/table states).

### C. Shared components that need visual design

Global navigation; Search form, filters, result card, pagination; Object Detail metadata; TRACE entry; Context controls and accessible rows; Spacetime controls/map/table; Validated Exploration controls/tree; fixed Open Inquiry disclosure; System Suggestions note; export controls; loading/zero/partial/error states.

### D. Mandatory product invariants

Search is homepage-level and mobile-capable. Search returns public object pages only. TRACE has exactly three functions and full runtime is desktop-only. Open Inquiry never implies validation. Guidance is visually secondary and provider identity is hidden. Object imagery is never assumed. Frontend actions may not change ranking, evidence, API schemas, data, rights, or mobile TRACE policy.

### E. Decisions Claude may make

Layout, hierarchy, spacing, typography, colour, motion, card treatment, map language, filter presentation, desktop navigation, mobile Search composition, responsive Object Detail treatment, and secondary guidance treatment.

### F. Decisions Claude may not make

Search ranking/eligibility/filter semantics; TRACE evidence; association validation; Open Inquiry status; API schemas; database content; rights decisions; TRACE mobile activation; or model behavior.

### G. Exact API subset Claude should consume

Use Section 16. The only optional route is System Suggestions. Never build screens for internal V3 controls, fail-closed V3 active routes, retired V1 Exploration, legacy compatibility routes, or server-support identity routes.

### H. Known limitations

Current Object Detail is metadata/citation-only. The current release has zero positive visual-rights records. V3 has zero production activations. Movement coverage is sparse. Context/Spacetime reference workspaces are functional but unlinked/no-index. External human review for Open Inquiry remains pending.

### I. Unresolved frontend design questions

Final navigation grouping for the two unlinked TRACE workspaces; exact visual system; safe visual expression of generated diagrams; presentation of the Object Detail citation state; and how to expose V2’s existing export actions without implying an image-rights grant.

## 25. Metric dictionary and source references

Each machine metric carries its exact definition, source path, SHA-256, and generation method. Primary inputs are the release data profile, Search manifest/documents/facets, Context and Spacetime manifests, V2/V3 read models, Open Inquiry registry, canonical product API map, and current filesystem route scan. Use `SOURCE_MANIFEST.json` for bounded implementation verification; do not scan the repository indiscriminately.
