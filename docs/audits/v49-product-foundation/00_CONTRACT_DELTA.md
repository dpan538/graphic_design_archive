# v49 Read Platform — core contract delta

Status: accepted only for the Phase 2C core implementation in this branch.

`READ_API_V1.md` fixes the endpoint families, exact-pair semantics, error
model, pagination and disclosure boundary, but intentionally describes most
DTOs as a positive allowlist rather than publishing field-by-field JSON
schemas.  This table records the smallest implementation choices so no page
or adapter infers fields from the frozen v48 payload.

| Area | Contract source | Core decision | Explicitly excluded |
|---|---|---|---|
| Research identity | ADR 0002, ADR 0003, Read API v1 | Every success has exact `researchReleaseId` and `researchManifestSha256`; the fixture uses one sealed pair. | Generic `version`, mutable `current` after provider resolution. |
| Visual identity | ADR 0002, Read API v1 | Core fixture is research-only: both visual fields are `null`, state is `UNAVAILABLE`, and a reason code is present. | Partial visual pairs and all remote image, thumbnail, IIIF, embed, proxy, `srcset` and media-locator fields. |
| Surface list/detail | Read API v1 archive DTO boundary | `surfaceId`, title, credited labels, display date/year, place, medium, type, source citation label/link, publication layer, and delivery state only. | Internal UUIDs, raw payload, workflow/review values, held locators, provider identity, database names and unrestricted source fields. |
| Folder | Read API v1 folder contract | ID, type, slug, title, narrative scope, exact member count; member rows are independently keyset-paginated. | Embedded membership arrays or unbounded IDs. |
| Search | Read API v1 search contract | `archive` discriminant only for the real fixture; case-folded title/credit/place/medium matching; stable title/id keyset sort. | Legacy search index, TRACE-derived population, opaque score provenance. |
| TRACE | Phase 1C/2A receipts, Read API v1 | Atlas contains named units with `totalExact=0`; object list is empty; neighborhood rejects ineligible IDs with a typed error. | Synthetic/nonzero TRACE, default edge, inferred influence, placeholder geometry or unknown relations. |
| Relation registry | Read API v1 | Empty published registry for the real fixture. Test-only synthetic cases exercise an unknown relation as `INTEGRITY_FAILURE`. | `OTHER` mapping or public unknown relation DTO. |

The delta is intentionally additive.  It neither alters release, rights,
identity or seal/CAS semantics nor claims the full Read API v1 field set.
